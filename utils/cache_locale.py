"""
cache_locale.py — Cache persistente dei dati fondamentali su Google Sheets.

Salva i dati scaricati da FMP/yfinance su un foglio Google separato.
Se i dati sono freschi (< MAX_AGE_ORE ore), li riusa senza chiamare l'API.
Risparmia fino a 200 chiamate FMP al giorno.
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict

MAX_AGE_ORE = 8   # dati validi per 8 ore

CACHE_SHEET  = "Screener_Cache"
CACHE_COLS   = [
    "ticker", "timestamp", "nome", "settore", "mktcap_M",
    "prezzo", "pe", "roe", "de_ratio", "gross_margin", "div_yield",
]


# ══════════════════════════════════════════════
# CONNESSIONE SHEET
# ══════════════════════════════════════════════

def _get_cache_sheet():
    """Apre (o crea) il foglio Cache su Google Sheets."""
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
            sh = client.open(CACHE_SHEET)
        except Exception:
            sh = client.create(CACHE_SHEET)
        try:
            ws = sh.worksheet("Fondamentali")
        except Exception:
            ws = sh.add_worksheet(title="Fondamentali", rows=5000, cols=len(CACHE_COLS))
            ws.append_row(CACHE_COLS)
        return ws
    except Exception:
        return None


def cache_disponibile() -> bool:
    """Controlla se Google Sheets è configurato (riusa la stessa check di storage.py)."""
    try:
        _ = st.secrets["gcp_service_account"]
        return True
    except Exception:
        return False


# ══════════════════════════════════════════════
# LETTURA CACHE
# ══════════════════════════════════════════════

@st.cache_data(ttl=900, show_spinner=False)   # cache in memoria 15 minuti
def _load_cache_df() -> pd.DataFrame:
    """Carica tutto il foglio Cache in un DataFrame."""
    ws = _get_cache_sheet()
    if ws is None:
        return pd.DataFrame(columns=CACHE_COLS)
    try:
        records = ws.get_all_records()
        if not records:
            return pd.DataFrame(columns=CACHE_COLS)
        df = pd.DataFrame(records)
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        for col in ["mktcap_M", "prezzo", "pe", "roe", "de_ratio", "gross_margin", "div_yield"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        return df
    except Exception:
        return pd.DataFrame(columns=CACHE_COLS)


def get_da_cache(ticker: str) -> Optional[Dict]:
    """
    Ritorna i dati fondamentali dalla cache se freschi.
    Ritorna None se non presenti o scaduti.
    """
    if not cache_disponibile():
        return None
    try:
        df = _load_cache_df()
        if df.empty:
            return None
        mask = df["ticker"].str.upper() == ticker.upper()
        rows = df[mask]
        if rows.empty:
            return None
        row = rows.sort_values("timestamp").iloc[-1]
        ts = row["timestamp"]
        if pd.isna(ts):
            return None
        if datetime.now() - ts.to_pydatetime() > timedelta(hours=MAX_AGE_ORE):
            return None
        return row.to_dict()
    except Exception:
        return None


# ══════════════════════════════════════════════
# SCRITTURA CACHE
# ══════════════════════════════════════════════

def salva_in_cache(dati: Dict) -> bool:
    """Salva i dati fondamentali di un ticker nella cache."""
    if not cache_disponibile():
        return False
    ws = _get_cache_sheet()
    if ws is None:
        return False
    try:
        row = [
            str(dati.get("ticker", "")),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            str(dati.get("nome", "")),
            str(dati.get("settore", "")),
            _safe(dati.get("mktcap_M")),
            _safe(dati.get("prezzo")),
            _safe(dati.get("pe")),
            _safe(dati.get("roe")),
            _safe(dati.get("de_ratio")),
            _safe(dati.get("gross_margin")),
            _safe(dati.get("div_yield")),
        ]
        ws.append_row(row)
        # Invalida cache in memoria
        _load_cache_df.clear()
        return True
    except Exception:
        return False


def svuota_cache() -> bool:
    """Svuota il foglio Cache (mantiene l'intestazione)."""
    ws = _get_cache_sheet()
    if ws is None:
        return False
    try:
        ws.clear()
        ws.append_row(CACHE_COLS)
        _load_cache_df.clear()
        return True
    except Exception:
        return False


def stato_cache() -> Dict:
    """Statistiche sulla cache corrente."""
    if not cache_disponibile():
        return {"disponibile": False}
    try:
        df = _load_cache_df()
        if df.empty:
            return {"disponibile": True, "totale": 0, "freschi": 0}
        soglia = datetime.now() - timedelta(hours=MAX_AGE_ORE)
        freschi = (df["timestamp"] > soglia).sum()
        return {
            "disponibile": True,
            "totale": len(df),
            "freschi": int(freschi),
            "scaduti": int(len(df) - freschi),
            "ultimo_aggiornamento": df["timestamp"].max().strftime("%d/%m %H:%M") if not df["timestamp"].isna().all() else "—",
        }
    except Exception:
        return {"disponibile": True, "totale": 0, "freschi": 0}


def _safe(val):
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return ""
    try:
        return round(float(val), 6)
    except Exception:
        return ""
