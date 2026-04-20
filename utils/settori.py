"""
settori.py — Analisi del momentum settoriale tramite ETF USA e europei.
Classifica ogni settore come Favorevole / Neutro / Sfavorevole
confrontando il rendimento 3M dell'ETF settoriale vs S&P 500.
"""

import yfinance as yf
import pandas as pd
import numpy as np
import streamlit as st
from typing import Dict

# ── ETF settoriali USA (SPDR Select Sector) ───────────────────
ETF_USA = {
    "Technology":             "XLK",
    "Healthcare":             "XLV",
    "Financials":             "XLF",
    "Consumer Discretionary": "XLY",
    "Consumer Staples":       "XLP",
    "Energy":                 "XLE",
    "Industrials":            "XLI",
    "Materials":              "XLB",
    "Utilities":              "XLU",
    "Real Estate":            "XLRE",
    "Communication":          "XLC",
}

# ── ETF settoriali Europa (iShares / Stoxx) ───────────────────
ETF_EU = {
    "Technology":    "IXN",
    "Healthcare":    "IXJ",
    "Financials":    "IXG",
    "Energy":        "IXC",
    "Industrials":   "EXI",
    "Consumer":      "RXI",
    "Materials":     "MXI",
    "Utilities":     "JXI",
}

BENCHMARK = "SPY"   # S&P 500 come benchmark di riferimento
PERIODO   = "6mo"   # finestra di analisi

# Soglie per classificazione
SOGLIA_FAVO  =  0.03   # +3% vs SPY → Favorevole
SOGLIA_SFAVO = -0.03   # -3% vs SPY → Sfavorevole


@st.cache_data(ttl=14400, show_spinner=False)   # cache 4 ore
def get_sector_momentum() -> Dict[str, dict]:
    """
    Scarica i prezzi degli ETF settoriali e del benchmark,
    calcola il rendimento relativo 3M e 6M, classifica ogni settore.

    Ritorna dict: { "Technology": {"ret_3m": 0.08, "rel_3m": 0.05,
                                    "status": "favorevole", "etf": "XLK"}, ... }
    """
    tutti_etf = list(ETF_USA.values()) + list(ETF_EU.values()) + [BENCHMARK]
    tutti_etf = list(set(tutti_etf))

    try:
        raw = yf.download(
            tutti_etf, period=PERIODO, interval="1d",
            auto_adjust=True, progress=False, threads=True,
        )
        if raw.empty:
            return {}

        if isinstance(raw.columns, pd.MultiIndex):
            close = raw["Close"]
        else:
            close = raw

    except Exception:
        return {}

    # Rendimento benchmark
    bench_ret = _calc_ret(close, BENCHMARK)

    risultati = {}
    for settore, etf in ETF_USA.items():
        if etf not in close.columns:
            continue
        ret_3m = _calc_ret(close, etf, giorni=63)
        ret_6m = _calc_ret(close, etf, giorni=126)
        if ret_3m is None:
            continue
        rel_3m = ret_3m - (bench_ret or 0)
        if rel_3m >= SOGLIA_FAVO:
            status = "favorevole"
        elif rel_3m <= SOGLIA_SFAVO:
            status = "sfavorevole"
        else:
            status = "neutro"
        risultati[settore] = {
            "ret_3m": round(ret_3m, 4),
            "ret_6m": round(ret_6m or 0, 4),
            "rel_3m": round(rel_3m, 4),
            "status": status,
            "etf":    etf,
        }

    return risultati


def _calc_ret(close: pd.DataFrame, ticker: str, giorni: int = 63) -> float | None:
    """Calcola il rendimento su N giorni di un ticker nel DataFrame close."""
    if ticker not in close.columns:
        return None
    series = close[ticker].dropna()
    if len(series) < giorni // 2:
        return None
    idx = max(0, len(series) - giorni)
    p_old = float(series.iloc[idx])
    p_new = float(series.iloc[-1])
    if p_old <= 0:
        return None
    return (p_new / p_old) - 1


def sector_status_label(status: str) -> str:
    """Etichetta leggibile per la UI."""
    return {
        "favorevole":  "🟢 Favorevole",
        "neutro":      "🟡 Neutro",
        "sfavorevole": "🔴 Sfavorevole",
    }.get(status, "⚪ N/D")


def sector_bonus(settore: str, momentum: Dict[str, dict]) -> float:
    """
    Ritorna un bonus/malus da applicare allo score Universe
    basato sul momentum del settore dell'azienda.
      +0.10 → settore favorevole
       0.00 → neutro o non trovato
      -0.10 → settore sfavorevole
    """
    if not settore or not momentum:
        return 0.0
    # Cerca corrispondenza parziale (es. "Information Technology" → "Technology")
    for key, data in momentum.items():
        if key.lower() in settore.lower() or settore.lower() in key.lower():
            return {"favorevole": 0.10, "neutro": 0.0, "sfavorevole": -0.10}.get(
                data["status"], 0.0
            )
    return 0.0


def build_sector_table(momentum: Dict[str, dict]) -> pd.DataFrame:
    """Costruisce un DataFrame ordinato per visualizzazione."""
    if not momentum:
        return pd.DataFrame()
    rows = []
    for settore, d in sorted(momentum.items(), key=lambda x: -x[1]["rel_3m"]):
        rows.append({
            "Settore":     settore,
            "ETF":         d["etf"],
            "Ret 3M":      d["ret_3m"],
            "Vs S&P 500":  d["rel_3m"],
            "Ret 6M":      d["ret_6m"],
            "Status":      sector_status_label(d["status"]),
        })
    return pd.DataFrame(rows)
