"""
Paper Trading — Portafoglio Virtuale
Registra operazioni ipotetiche con prezzi reali e traccia la performance.
Storage su Google Sheets.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import yfinance as yf
from utils.storage import gdrive_available
from utils.data import fetch_price_history

# ══════════════════════════════════════════════
# STORAGE SU GOOGLE SHEETS
# ══════════════════════════════════════════════

PT_SHEET  = "Screener_PaperTrading"
PT_COLS   = ["id", "data_apertura", "ticker", "nome", "direzione",
             "quantita", "prezzo_entrata", "prezzo_uscita",
             "data_uscita", "stato", "note", "score_entrata"]


def _get_pt_sheet():
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = Credentials.from_service_account_info(
            dict(st.secrets["gcp_service_account"]), scopes=scopes
        )
        client = gspread.authorize(creds)
        try:
            sh = client.open(PT_SHEET)
        except Exception:
            sh = client.create(PT_SHEET)
        try:
            ws = sh.worksheet("Operazioni")
        except Exception:
            ws = sh.add_worksheet(title="Operazioni", rows=2000, cols=len(PT_COLS))
            ws.append_row(PT_COLS)
        return ws
    except Exception:
        return None


@st.cache_data(ttl=300, show_spinner=False)
def _load_operazioni() -> pd.DataFrame:
    ws = _get_pt_sheet()
    if ws is None:
        return pd.DataFrame(columns=PT_COLS)
    try:
        records = ws.get_all_records()
        if not records:
            return pd.DataFrame(columns=PT_COLS)
        df = pd.DataFrame(records)
        df["data_apertura"] = pd.to_datetime(df["data_apertura"], errors="coerce")
        df["data_uscita"]   = pd.to_datetime(df["data_uscita"],   errors="coerce")
        for col in ["quantita", "prezzo_entrata", "prezzo_uscita", "score_entrata"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        return df
    except Exception:
        return pd.DataFrame(columns=PT_COLS)


def _salva_operazione(op: dict) -> bool:
    ws = _get_pt_sheet()
    if ws is None:
        return False
    try:
        row = [str(op.get(c, "")) for c in PT_COLS]
        ws.append_row(row)
        _load_operazioni.clear()
        return True
    except Exception:
        return False


def _aggiorna_uscita(op_id: str, prezzo_uscita: float, note: str = "") -> bool:
    ws = _get_pt_sheet()
    if ws is None:
        return False
    try:
        cell = ws.find(str(op_id))
        if not cell:
            return False
        row = cell.row
        # Colonne: id=1, ..., prezzo_uscita=7, data_uscita=9, stato=10, note=11
        ws.update_cell(row, PT_COLS.index("prezzo_uscita") + 1, prezzo_uscita)
        ws.update_cell(row, PT_COLS.index("data_uscita")   + 1, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        ws.update_cell(row, PT_COLS.index("stato")         + 1, "Chiusa")
        if note:
            ws.update_cell(row, PT_COLS.index("note") + 1, note)
        _load_operazioni.clear()
        return True
    except Exception:
        return False


# ══════════════════════════════════════════════
# CALCOLI PERFORMANCE
# ══════════════════════════════════════════════

def calc_pnl(row: pd.Series, prezzo_attuale: float = None) -> dict:
    """Calcola P&L di una posizione."""
    p_in  = row["prezzo_entrata"]
    qty   = row["quantita"]
    stato = str(row["stato"])

    if stato == "Chiusa":
        p_out = row["prezzo_uscita"]
    elif prezzo_attuale:
        p_out = prezzo_attuale
    else:
        return {"pnl": None, "pnl_pct": None, "valore_attuale": None}

    if not p_in or not qty or not p_out:
        return {"pnl": None, "pnl_pct": None, "valore_attuale": None}

    pnl     = (p_out - p_in) * qty
    pnl_pct = (p_out / p_in - 1)
    valore  = p_out * qty

    return {"pnl": pnl, "pnl_pct": pnl_pct, "valore_attuale": valore,
            "costo": p_in * qty}


# ══════════════════════════════════════════════
# UI
# ══════════════════════════════════════════════

st.title("📈 Paper Trading — Portafoglio Virtuale")
st.caption("Registra operazioni ipotetiche con prezzi reali e monitora la performance nel tempo.")

if not gdrive_available():
    st.error("Google Sheets non configurato. Il paper trading richiede Google Sheets per salvare le operazioni.")
    with st.expander("Come configurarlo"):
        st.markdown("Consulta la sezione ⭐ Preferiti → guida configurazione Google Sheets.")
    st.stop()

# Carica operazioni
if st.session_state.get("pt_refresh"):
    _load_operazioni.clear()
    st.session_state["pt_refresh"] = False

df_op = _load_operazioni()

# ── STATISTICHE PORTAFOGLIO ───────────────────────────────────
st.subheader("📊 Riepilogo Portafoglio")

aperte  = df_op[df_op["stato"] == "Aperta"]  if not df_op.empty else pd.DataFrame()
chiuse  = df_op[df_op["stato"] == "Chiusa"]  if not df_op.empty else pd.DataFrame()

# Aggiorna prezzi attuali per posizioni aperte
prezzi_attuali = {}
if not aperte.empty:
    tickers_aperti = aperte["ticker"].dropna().unique().tolist()
    try:
        raw = yf.download(tickers_aperti, period="5d", interval="1d",
                          auto_adjust=True, progress=False)
        if not raw.empty:
            if isinstance(raw.columns, pd.MultiIndex):
                close_now = raw["Close"].iloc[-1]
            else:
                close_now = raw["Close"]
            for t in tickers_aperti:
                if t in close_now.index:
                    prezzi_attuali[t] = float(close_now[t])
    except Exception:
        pass

# Calcola P&L totale
pnl_aperte = 0
pnl_chiuse = 0
investito  = 0

for _, row in aperte.iterrows():
    p = prezzi_attuali.get(row["ticker"])
    r = calc_pnl(row, p)
    if r["pnl"] is not None:
        pnl_aperte += r["pnl"]
        investito  += r.get("costo", 0)

for _, row in chiuse.iterrows():
    r = calc_pnl(row)
    if r["pnl"] is not None:
        pnl_chiuse += r["pnl"]

pnl_totale = pnl_aperte + pnl_chiuse
n_vinci = 0
n_perdi = 0
for _, row in chiuse.iterrows():
    r = calc_pnl(row)
    if r["pnl"] is not None:
        if r["pnl"] >= 0: n_vinci += 1
        else: n_perdi += 1

win_rate = n_vinci / (n_vinci + n_perdi) * 100 if (n_vinci + n_perdi) > 0 else 0

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Posizioni Aperte",  len(aperte))
m2.metric("Posizioni Chiuse",  len(chiuse))
m3.metric("P&L Totale",
          f"${pnl_totale:+,.2f}" if df_op is not None and not df_op.empty else "—",
          delta=f"${pnl_totale:+,.2f}")
m4.metric("P&L Posizioni Aperte", f"${pnl_aperte:+,.2f}" if not aperte.empty else "—")
m5.metric("Win Rate", f"{win_rate:.0f}%" if (n_vinci + n_perdi) > 0 else "—")

# ── POSIZIONI APERTE ─────────────────────────────────────────
st.divider()
st.subheader("🔵 Posizioni Aperte")

if aperte.empty:
    st.info("Nessuna posizione aperta. Apri una nuova operazione qui sotto.")
else:
    righe = []
    for _, row in aperte.iterrows():
        p_att = prezzi_attuali.get(row["ticker"])
        r = calc_pnl(row, p_att)
        righe.append({
            "Ticker":        row["ticker"],
            "Nome":          row.get("nome", ""),
            "Data Apertura": row["data_apertura"].strftime("%d/%m/%Y") if pd.notna(row["data_apertura"]) else "—",
            "Qtà":           row["quantita"],
            "P. Entrata":    row["prezzo_entrata"],
            "P. Attuale":    round(p_att, 2) if p_att else None,
            "P&L $":         round(r["pnl"], 2) if r["pnl"] else None,
            "P&L %":         r["pnl_pct"],
            "ID":            row["id"],
        })
    df_aperte_show = pd.DataFrame(righe)
    st.dataframe(
        df_aperte_show.drop(columns=["ID"]),
        use_container_width=True, hide_index=True,
        column_config={
            "P. Entrata": st.column_config.NumberColumn("P. Entrata", format="$%.2f"),
            "P. Attuale": st.column_config.NumberColumn("P. Attuale", format="$%.2f"),
            "P&L $":      st.column_config.NumberColumn("P&L $", format="$%+.2f"),
            "P&L %":      st.column_config.NumberColumn("P&L %", format="%+.1f%%"),
        }
    )
    # Chiudi posizione
    with st.expander("🔴 Chiudi una posizione"):
        ids = df_aperte_show["ID"].tolist()
        tickers_ap = df_aperte_show["Ticker"].tolist()
        opts = [f"{t} (ID: {i})" for t, i in zip(tickers_ap, ids)]
        sel = st.selectbox("Seleziona posizione da chiudere", opts, key="sel_close")
        if sel:
            sel_id  = sel.split("ID: ")[1].rstrip(")")
            sel_tkr = sel.split(" ")[0]
            p_sug   = prezzi_attuali.get(sel_tkr, 0)
            p_out   = st.number_input("Prezzo di uscita", value=float(p_sug or 0),
                                      min_value=0.0, step=0.01, key="p_out")
            note_ch = st.text_input("Note chiusura", key="note_close")
            if st.button("✅ Conferma chiusura", key="btn_close"):
                ok = _aggiorna_uscita(sel_id, p_out, note_ch)
                if ok:
                    st.success("Posizione chiusa!")
                    st.session_state["pt_refresh"] = True
                    st.rerun()

# ── APRI NUOVA OPERAZIONE ─────────────────────────────────────
st.divider()
st.subheader("➕ Apri Nuova Operazione")

wl_tickers = st.session_state.get("watchlist_tickers", [])

col_a, col_b = st.columns([3, 2])
with col_a:
    if wl_tickers:
        ticker_new = st.selectbox("Ticker", options=wl_tickers, key="pt_ticker")
    else:
        ticker_new = st.text_input("Ticker (es. AAPL)", key="pt_ticker_free").upper().strip()

    nome_new    = st.text_input("Nome azienda (opzionale)", key="pt_nome")
    quantita    = st.number_input("Quantità azioni", min_value=1, value=10, step=1, key="pt_qty")
    prezzo_in   = st.number_input("Prezzo di entrata ($)", min_value=0.01,
                                   value=100.0, step=0.01, key="pt_price")
    note_new    = st.text_input("Note (motivo dell'operazione)", key="pt_note")

    # Score dall'ultima watchlist
    wl_data = st.session_state.get("watchlist_data")
    score_in = None
    if wl_data is not None and ticker_new in wl_data.index:
        score_in = float(wl_data.loc[ticker_new, "score"] or 0)
        st.caption(f"Score attuale dalla Watchlist: **{score_in:.3f}**")

with col_b:
    st.write("")
    st.write("")
    controvalore = prezzo_in * quantita if prezzo_in and quantita else 0
    st.metric("Controvalore", f"${controvalore:,.2f}")

    if st.button("🚀 Apri Posizione", type="primary", use_container_width=True, key="btn_open"):
        if not ticker_new:
            st.warning("Inserisci un ticker.")
        else:
            nuovo_id = datetime.now().strftime("%Y%m%d%H%M%S")
            op = {
                "id":            nuovo_id,
                "data_apertura": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "ticker":        ticker_new.upper(),
                "nome":          nome_new or ticker_new,
                "direzione":     "Long",
                "quantita":      quantita,
                "prezzo_entrata":round(prezzo_in, 4),
                "prezzo_uscita": "",
                "data_uscita":   "",
                "stato":         "Aperta",
                "note":          note_new,
                "score_entrata": round(score_in, 4) if score_in else "",
            }
            ok = _salva_operazione(op)
            if ok:
                st.success(f"✅ Posizione aperta: {ticker_new} × {quantita} a ${prezzo_in:.2f}")
                st.session_state["pt_refresh"] = True
                st.rerun()
            else:
                st.error("Errore nel salvataggio. Controlla Google Sheets.")

# ── STORICO CHIUSE ────────────────────────────────────────────
st.divider()
st.subheader("📋 Storico Posizioni Chiuse")

if chiuse.empty:
    st.info("Nessuna posizione chiusa ancora.")
else:
    righe_ch = []
    for _, row in chiuse.iterrows():
        r = calc_pnl(row)
        giorni = None
        if pd.notna(row["data_apertura"]) and pd.notna(row["data_uscita"]):
            giorni = (row["data_uscita"] - row["data_apertura"]).days
        righe_ch.append({
            "Ticker":       row["ticker"],
            "Data Ap.":     row["data_apertura"].strftime("%d/%m/%Y") if pd.notna(row["data_apertura"]) else "—",
            "Data Ch.":     row["data_uscita"].strftime("%d/%m/%Y") if pd.notna(row["data_uscita"]) else "—",
            "Giorni":       giorni,
            "P. Entrata":   row["prezzo_entrata"],
            "P. Uscita":    row["prezzo_uscita"],
            "Qtà":          row["quantita"],
            "P&L $":        round(r["pnl"], 2) if r["pnl"] is not None else None,
            "P&L %":        r["pnl_pct"],
            "Score Entrata":row.get("score_entrata"),
            "Note":         row.get("note", ""),
        })

    df_ch = pd.DataFrame(righe_ch)
    st.dataframe(
        df_ch,
        use_container_width=True, hide_index=True,
        column_config={
            "P. Entrata":    st.column_config.NumberColumn("P. Entrata",  format="$%.2f"),
            "P. Uscita":     st.column_config.NumberColumn("P. Uscita",   format="$%.2f"),
            "P&L $":         st.column_config.NumberColumn("P&L $",       format="$%+.2f"),
            "P&L %":         st.column_config.NumberColumn("P&L %",       format="%+.1f%%"),
            "Score Entrata": st.column_config.NumberColumn("Score",       format="%.3f"),
        }
    )

    # Grafico P&L cumulativo
    if len(df_ch) >= 2:
        with st.expander("📈 P&L Cumulativo", expanded=True):
            df_ch_sorted = df_ch.dropna(subset=["P&L $"]).sort_values("Data Ch.")
            df_ch_sorted["P&L Cumul."] = df_ch_sorted["P&L $"].cumsum()
            colors_bar = ["#2d7a2d" if v >= 0 else "#c0392b" for v in df_ch_sorted["P&L $"]]

            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=df_ch_sorted["Ticker"] + " " + df_ch_sorted["Data Ch."],
                y=df_ch_sorted["P&L $"],
                marker_color=colors_bar,
                name="P&L singolo",
            ))
            fig.add_trace(go.Scatter(
                x=df_ch_sorted["Ticker"] + " " + df_ch_sorted["Data Ch."],
                y=df_ch_sorted["P&L Cumul."],
                mode="lines+markers",
                name="P&L cumulativo",
                line=dict(color="#1a5276", width=2.5),
                yaxis="y2",
            ))
            fig.update_layout(
                height=320,
                yaxis2=dict(overlaying="y", side="right"),
                margin=dict(l=10, r=40, t=20, b=80),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="#f9f9f9",
                legend=dict(orientation="h"),
                xaxis=dict(tickangle=-30),
            )
            fig.add_hline(y=0, line_dash="dash", line_color="#999")
            st.plotly_chart(fig, use_container_width=True)
