"""
Screener Azioni USA & Europa — Medio Periodo
Applicazione Streamlit per ricerca di opportunità di investimento.
"""

import streamlit as st

st.set_page_config(
    page_title="Screener Azioni",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": "Screener Azioni USA & Europa — Ricerca diamanti grezzi",
    },
)

# ── CSS globale per mobile + stile ──────────────────────
st.markdown("""
<style>
/* Font base */
html, body, [class*="css"] { font-family: 'Segoe UI', sans-serif; }

/* Sidebar più stretta su desktop */
[data-testid="stSidebar"] { min-width: 220px; max-width: 260px; }

/* Tabelle scrollabili su mobile */
[data-testid="stDataFrame"] { overflow-x: auto !important; }

/* Bottoni primari */
.stButton > button {
    border-radius: 8px;
    font-weight: 600;
    padding: 0.4rem 1.2rem;
}

/* Metriche più compatte */
[data-testid="metric-container"] {
    background: #f0f2f6;
    border-radius: 8px;
    padding: 0.5rem !important;
}

/* Colori tier badge */
.tier-alta  { background:#C6EFCE; color:#276221; padding:2px 8px; border-radius:12px; font-weight:700; }
.tier-media { background:#FFEB9C; color:#7D5A00; padding:2px 8px; border-radius:12px; font-weight:700; }
.tier-bassa { background:#FFC7CE; color:#9C0006; padding:2px 8px; border-radius:12px; font-weight:700; }

/* Nasconde footer Streamlit */
footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── Inizializzazione session state globale ───────────────
def _init_state():
    defaults = {
        "watchlist_tickers":  [],           # lista ticker in Watchlist
        "watchlist_data":     None,         # DataFrame dati watchlist
        "universe_data":      None,         # DataFrame Universe corrente
        "universe_selection": [],           # ticker selezionati in Universe
        "preferiti_df":       None,         # cache DataFrame Preferiti
        "last_update":        None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

_init_state()

# ── Navigazione ──────────────────────────────────────────
pg = st.navigation([
    st.Page("pages/universe.py",       title="🌍 Universe",          icon="🌍", default=True),
    st.Page("pages/diamond_hunter.py", title="💎 Diamond Hunter",    icon="💎"),
    st.Page("pages/watchlist.py",      title="📋 Watchlist",         icon="📋"),
    st.Page("pages/dashboard.py",      title="🏆 Dashboard",         icon="🏆"),
    st.Page("pages/price_targets.py",  title="🎯 Price Targets",     icon="🎯"),
    st.Page("pages/storico.py",        title="📈 Storico Prezzi",    icon="📈"),
    st.Page("pages/dividendi.py",      title="💰 Dividendi",         icon="💰"),
    st.Page("pages/preferiti.py",      title="⭐ Preferiti",         icon="⭐"),
    st.Page("pages/paper_trading.py",  title="📊 Paper Trading",     icon="📊"),
    st.Page("pages/ml_insights.py",    title="🧠 ML Insights",       icon="🧠"),
    st.Page("pages/notifiche.py",      title="🔔 Notifiche",         icon="🔔"),
])
pg.run()
