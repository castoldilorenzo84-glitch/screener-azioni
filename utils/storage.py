"""
storage.py — Gestione Google Sheets per la memoria storica (Preferiti)
Usa gspread con Service Account memorizzato in st.secrets.
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional, List, Dict

SHEET_NAME_DEFAULT = "Screener_Preferiti"
COLUMNS = [
    "ticker", "nome", "settore", "data_snapshot",
    "prezzo", "ret_6m", "ret_12m", "vol_ann",
    "pe", "roe", "de_ratio", "gross_margin", "div_yield",
    "score", "tier", "percentile", "note", "fonte",
]


def _get_client():
    """Crea e ritorna un client gspread autenticato via Service Account."""
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        creds_info = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
        return gspread.authorize(creds)
    except Exception as e:
        return None


def _get_sheet():
    """Apre (o crea) il Google Sheet dei Preferiti."""
    client = _get_client()
    if client is None:
        return None
    sheet_name = st.secrets.get("GSHEET_NAME", SHEET_NAME_DEFAULT)
    try:
        sh = client.open(sheet_name)
    except Exception:
        try:
            sh = client.create(sheet_name)
        except Exception:
            return None
    # Assicura che esista il foglio "Preferiti"
    try:
        ws = sh.worksheet("Preferiti")
    except Exception:
        ws = sh.add_worksheet(title="Preferiti", rows=5000, cols=len(COLUMNS))
        ws.append_row(COLUMNS)
    return ws


def gdrive_available() -> bool:
    """Controlla se la connessione a Google Sheets è configurata."""
    try:
        _ = st.secrets["gcp_service_account"]
        return True
    except Exception:
        return False


def load_preferiti() -> pd.DataFrame:
    """Carica tutti i snapshot da Google Sheets."""
    ws = _get_sheet()
    if ws is None:
        return pd.DataFrame(columns=COLUMNS)
    try:
        records = ws.get_all_records()
        if not records:
            return pd.DataFrame(columns=COLUMNS)
        df = pd.DataFrame(records)
        # Assicura che tutte le colonne esistano
        for col in COLUMNS:
            if col not in df.columns:
                df[col] = None
        df["data_snapshot"] = pd.to_datetime(df["data_snapshot"], errors="coerce")
        # Tipi numerici
        for col in ["prezzo", "ret_6m", "ret_12m", "vol_ann", "pe", "roe",
                    "de_ratio", "gross_margin", "div_yield", "score", "percentile"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        return df[COLUMNS]
    except Exception:
        return pd.DataFrame(columns=COLUMNS)


def save_snapshot(ticker_data: dict, note: str = "", fonte: str = "manuale") -> bool:
    """
    Salva uno snapshot del ticker nel Google Sheet.
    ticker_data deve contenere tutti i campi chiave.
    """
    ws = _get_sheet()
    if ws is None:
        return False
    try:
        row = [
            str(ticker_data.get("ticker", "")),
            str(ticker_data.get("nome", "")),
            str(ticker_data.get("settore", "")),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            _safe_num(ticker_data.get("prezzo")),
            _safe_num(ticker_data.get("ret_6m")),
            _safe_num(ticker_data.get("ret_12m")),
            _safe_num(ticker_data.get("vol_ann")),
            _safe_num(ticker_data.get("pe")),
            _safe_num(ticker_data.get("roe")),
            _safe_num(ticker_data.get("de_ratio")),
            _safe_num(ticker_data.get("gross_margin")),
            _safe_num(ticker_data.get("div_yield")),
            _safe_num(ticker_data.get("score")),
            str(ticker_data.get("tier", "")),
            _safe_num(ticker_data.get("percentile")),
            str(note),
            str(fonte),
        ]
        ws.append_row(row)
        return True
    except Exception:
        return False


def save_snapshots_bulk(rows: List[dict], fonte: str = "watchlist") -> int:
    """Salva più snapshot in bulk. Ritorna numero di righe salvate."""
    ws = _get_sheet()
    if ws is None:
        return 0
    saved = 0
    for row_data in rows:
        if save_snapshot(row_data, fonte=fonte):
            saved += 1
    return saved


def delete_ticker_history(ticker: str) -> bool:
    """Rimuove tutte le righe di un ticker dai Preferiti."""
    ws = _get_sheet()
    if ws is None:
        return False
    try:
        all_data = ws.get_all_values()
        if not all_data or len(all_data) < 2:
            return True
        header = all_data[0]
        ticker_col = header.index("ticker") if "ticker" in header else 0
        # Trova righe da eliminare (dal basso verso l'alto per non spostare gli indici)
        rows_to_delete = [
            i + 1  # 1-indexed per gspread
            for i, row in enumerate(all_data[1:], start=1)
            if len(row) > ticker_col and row[ticker_col].upper() == ticker.upper()
        ]
        for row_idx in sorted(rows_to_delete, reverse=True):
            ws.delete_rows(row_idx + 1)  # +1 perché gspread è 1-indexed
        return True
    except Exception:
        return False


def get_ticker_evolution(ticker: str, df: pd.DataFrame = None) -> pd.DataFrame:
    """
    Ritorna l'evoluzione storica di un ticker (tutti gli snapshot).
    Se df è fornito, filtra da lì; altrimenti carica da Sheets.
    """
    if df is None:
        df = load_preferiti()
    if df.empty:
        return pd.DataFrame()
    mask = df["ticker"].str.upper() == ticker.upper()
    evo = df[mask].sort_values("data_snapshot").copy()
    return evo


def get_latest_snapshot(ticker: str, df: pd.DataFrame = None) -> Optional[dict]:
    """Ritorna l'ultimo snapshot di un ticker."""
    evo = get_ticker_evolution(ticker, df)
    if evo.empty:
        return None
    return evo.iloc[-1].to_dict()


def get_tracked_tickers(df: pd.DataFrame = None) -> List[str]:
    """Lista dei ticker distinti nei Preferiti."""
    if df is None:
        df = load_preferiti()
    if df.empty:
        return []
    return sorted(df["ticker"].dropna().unique().tolist())


def _safe_num(val):
    """Converte a float sicuro, ritorna stringa vuota se None/NaN."""
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return ""
    try:
        return round(float(val), 6)
    except Exception:
        return ""
